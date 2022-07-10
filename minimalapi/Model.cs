using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using Azure;
using Azure.Data.Tables;

class Folder {
    public Folder() {
        this.Id = String.Empty;
        this.Name = String.Empty;
        this.Description = String.Empty;
        this.Children = new List<Folder>();
    }
    public Folder(string name) {
        this.Id = CreateFolderUniqueId();
        this.Name = name;
        this.Description = String.Empty;
        this.Children = new List<Folder>();
    }

    public Folder(string id, string name) {
        this.Id = id;
        this.Name = name;
        this.Description = String.Empty;
        this.Children = new List<Folder>();
    }

    public string Id { get; set; }
    public string Name { get; set; }
    [JsonIgnore] public string Path { get { 
        if ( this.Parent == null ) // we're root
            return "/";
        else {
            string path = "/" + this.Name;
            Folder? node = this.Parent;
            while ( node != null ) {
                path = node.Parent != null ? "/" + node.Name + path : path;
                node = node.Parent;
            }
            return path;
        }
    } }
    [JsonIgnore] public string? ParentId { get; set; }
    [JsonIgnore] public List<Folder> Children { get; set; }

    [JsonIgnore] public Folder? Parent { get; set; }
    public Boolean HasChildren { get { return this.Children.Count > 0; } }
    public string Description { get; set; }

    public Folder GetRoot() {
        Folder current = this;
        while (current.Parent != null) {
            current = current.Parent;
        }
        return current;
    }

    public Folder AddChild(Folder child) {
        child.Parent = this;

        Folder root = this.GetRoot();
        while(!IsIdUnique(root, child.Id)) {
            child.Id = CreateFolderUniqueId();
        }

        this.Children.Add(child);
        this.Children.Sort((a, b) => a.Name.CompareTo(b.Name));

        return child;
    }

    public static string CreateFolderUniqueId() {
        const int FOLDER_ID_LENGTH = 7;
        return IDGenerator.Generate(FOLDER_ID_LENGTH);
    }
    public static bool IsIdUnique(Folder root, string id) {
        // Check the folder itself
        if (root.Id == id) {
            return false;
        }
        // Check all children
        foreach (var child in root.Children) {
            if (!IsIdUnique(child, id)) {
                return false;
            }
        }
        // This is unique
        return true;
    }
    public static Folder? FindFolderById(Folder root, string id) {
        // Check the folder itself
        if (root.Id == id) {
            return root;
        }
        // Check all children
        foreach (var child in root.Children) {
            var found = FindFolderById(child, id);
            if (found != null) {
                return found;
            }
        }
        // This is not found
        return null;
    }

    public static Folder? FindFolderByPath(Folder start, string path) {
        Folder? node = start;

        // check if this is an absolute path, if so start from root
        if ( path[0] == '/' )
            node = start.GetRoot();

        // move to the next folder in the path
        foreach ( var p in path.Split('/') ) {
            if (p == "") {
                continue;
            }
            node = node.Children.Find(f => f.Name == p);
            if (node == null) {
                return null;
            }
        }

        return node;
    }

    public static Folder CreateFolder(Folder parent, string path, string connectionString) {
        Debug.Assert(parent != null);
        Debug.Assert(path != null && path.Length > 0);

        // Check if this is a relative or absolute path and move to root
        // if absolute
        if ( path[0] == '/' ) 
            parent = parent.GetRoot();

        // Split the path and make sure each level exist
        var parts = path.Split('/');
        for (int i = 0; i < parts.Length; i++) {
            var part = parts[i];
            if (part == "") {
                continue;
            }
            var child = parent.Children.Find(f => f.Name == part);
            if (child == null) {
                child = new Folder(part);
                parent.AddChild(child);
                InsertFolderIntoAzureTable(parent, child, connectionString);
            }
            parent = child;
        }

        return parent; // this is now the new child
    }

    private static void InsertFolderIntoAzureTable(Folder parent, Folder child, string connectionString) {
        // Write new folder into Azure table
        var serviceClient = new TableServiceClient(connectionString);
        var tableClient = serviceClient.GetTableClient("forest");
        FolderEntity newEntity = new FolderEntity();
        newEntity.PartitionKey = "folder";
        newEntity.RowKey = child.Id;
        newEntity.Parent = parent.Id;
        newEntity.Name = child.Name;
        tableClient.UpsertEntity(newEntity);
    }

    public static bool CanDeleteFolder(Folder folder) {
        // cannot delete if it has children
        if (folder.Children.Count > 0) {
            return false;
        }
        // cannot delete if it is the root
        if (folder.Parent == null) {
            return false;
        }
        // can delete
        return true;
    }

    public static void DeleteFolder(Folder folder) {
        Debug.Assert(folder != null);
        Debug.Assert(folder.Parent != null);
        Debug.Assert(CanDeleteFolder(folder));

        if ( CanDeleteFolder(folder) ) {
            folder.Parent.Children.Remove(folder);
        } else {
            throw new ApplicationException("Cannot delete folder");
        }
    }

    public static void DeleteFolder(Folder parent, string path) {
        Debug.Assert(parent != null);
        Debug.Assert(path != null && path.Length > 0);

        Folder? folderToDelete = Folder.FindFolderByPath(parent, path);
        if ( folderToDelete == null ) {
            throw new ApplicationException("Cannot find folder to delete");
        } else {
            DeleteFolder(folderToDelete);
        }
    }

    public static Folder LoadModelFromTable(string connectionString) {
        const string TABLENAME = "forest";
        const string PARTITION_KEY = "folder";

        // read from azure table
        var serviceClient = new TableServiceClient(connectionString);
        var tableClient = serviceClient.GetTableClient(TABLENAME);
        var results = tableClient.Query<FolderEntity>(filter: $"PartitionKey eq '{PARTITION_KEY}'");

        // the database may be empty, so then just imitate a root folder
        List<FolderEntity> allfolders = results.ToList<FolderEntity>();
        if ( allfolders.Count() == 0 ) {
            Folder newRoot = new Folder("/");
            // TODO: Insert this into the db
            return newRoot;
        }

        // create root, update with info from db
        Folder root = new Folder("/");
        FolderEntity? rootEntity = allfolders.Find(f => f.Name == "/");
        if ( rootEntity != null ) {
            root.Id = rootEntity.RowKey;
            allfolders.Remove(rootEntity);
        }

        // now walk all other folders and add them to the tree
        AddChildFolders(root, allfolders);
        Debug.Assert(allfolders.Count() == 0); // we should have placed all folders, rest are orphans and somethings off
        if ( allfolders.Count() > 0 ) {
            Folder orphans = root.AddChild( new Folder("_orphans") );
            allfolders.ForEach( f => orphans.AddChild( new Folder(f.RowKey, f.Name) ) );
        }
        return root;
    }

    static void AddChildFolders(Folder parent, List<FolderEntity> allfolders) {
        var children = allfolders.FindAll(f => f.Parent == parent.Id);
        foreach (var child in children) {
            Folder folder = new Folder(child.RowKey, child.Name);
            folder.ParentId = child.Parent;
            parent.AddChild(folder);
            allfolders.Remove(child);
            AddChildFolders(folder, allfolders);
        }
    }

    public List<File> ListAllFiles(string connectionString) {
        const string TABLENAME = "folders";

        // read from azure table
        var serviceClient = new TableServiceClient(connectionString);
        var tableClient = serviceClient.GetTableClient(TABLENAME);
        var results = tableClient.Query<FileInFolderEntity>(filter: $"PartitionKey eq '{this.Id}'");

        // the database may be empty, so then just imitate a root folder
        List<FileInFolderEntity> allfiles = results.ToList<FileInFolderEntity>();

        // create root, update with info from db
        List<File> files = new List<File>(allfiles.Count());
        foreach (var file in allfiles) {
            files.Add(new File(file.RowKey, file.name));
        }
        return files;
    }
};

class FolderEntity : ITableEntity {
    public FolderEntity() {
        this.PartitionKey = this.RowKey = String.Empty;
        this.Timestamp = DateTime.Now;
        this.ETag = new ETag();
        this.Name = this.Parent = String.Empty;
    }
    public string PartitionKey { get; set; }
    public string RowKey { get; set; }
    public DateTimeOffset? Timestamp { get; set; }
    public ETag ETag { get; set; }
    public string Parent { get; set; }
    public string Name { get; set; }
    // implement tostring for this object
    public override string ToString() {
        return $"{this.Name} ({this.RowKey}) {this.Parent}";
    }
};

class FileInFolderEntity : ITableEntity {
    public FileInFolderEntity() {
        this.PartitionKey = this.RowKey = this.name = String.Empty;
        this.Timestamp = DateTime.Now;
        this.ETag = new ETag();
    }
    public string PartitionKey { get; set; }
    public string RowKey { get; set; }
    public DateTimeOffset? Timestamp { get; set; }
    public ETag ETag { get; set; }
    public string name { get; set; }
};

class FileEntity : ITableEntity
{
    public FileEntity() {
        this.PartitionKey = this.RowKey = this.name = String.Empty;
        this.Timestamp = DateTime.Now;
        this.ETag = new ETag();
    }
    public string PartitionKey { get; set; }
    public string RowKey { get; set; }
    public DateTimeOffset? Timestamp { get; set; }
    public ETag ETag { get; set; }
    public string name { get; set; }
}

class File {
    public File(string id, string name) {
        this.Id = id;
        this.Name = name;
    }
    public string Id { get; set; }
    public string Name { get; set; }

    public static File? LookupFileById(string id, string connectionString) {
        const string TABLENAME = "files";

        // check correct form on the id
        if ( !Regex.IsMatch(id, "^[a-zA-Z0-9]{3}-[a-zA-Z0-9]{7}$") )
            return null;

        var idParts = id.Split('-');

        // read from azure table
        var serviceClient = new TableServiceClient(connectionString);
        var tableClient = serviceClient.GetTableClient(TABLENAME);
        var results = tableClient.Query<FileEntity>(filter: $"PartitionKey eq '{idParts[0]}' and RowKey eq '{id}'");
        var file = results.FirstOrDefault();
        if ( file == null ) 
            return null;

        return new File(file.RowKey, file.name);
    }
    
    public override string ToString() {
        return $"{this.Name} ({this.Id})";
    }
};