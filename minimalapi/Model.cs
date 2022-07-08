using System.Collections;
using System.Collections.Generic;
using System.Text.Json.Serialization;

class Folder {
    // constructor
    public Folder(string name) {
        this.Id = CreateFolderUniqueId();
        this.Name = name;
        this.Children = new List<Folder>();
    }

    public Folder(string id, string name) {
        this.Id = id;
        this.Name = name;
        this.Children = new List<Folder>();
    }

    public string Id { get; set; }
    public string Name { get; set; }
    [JsonIgnore] public string? ParentId { get; set; }
    [JsonIgnore] public List<Folder> Children { get; set; }

    [JsonIgnore] public Folder? Parent { get; set; }
    public Folder GetRoot() {
        Folder current = this;
        while (current.Parent != null) {
            current = current.Parent;
        }
        return current;
    }

    public Folder AddChild(Folder child) {
        child.Parent = this;
        this.Children.Add(child);

        Folder root = this.GetRoot();
        while(!IsIdUnique(root,child.Id)) {
            child.Id = CreateFolderUniqueId();
        }

        return child;
    }

    public static string CreateFolderUniqueId() {
        return IDGenerator.Generate(7);
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

    public static Folder? FindFolderByPath(Folder root, string path) {
        Folder? node = root;
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
};

class File {
    public File(string id, string name) {
        this.Id = id;
        this.Name = name;
    }
    public string Id { get; set; }
    public string Name { get; set; }
};