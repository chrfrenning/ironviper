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

    public string Id { get; set; }
    public string Name { get; set; }
    [JsonIgnore] public string? ParentId { get; set; }
    [JsonIgnore] public List<Folder> Children { get; set; }

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
};

class File {
    public File(string id, string name) {
        this.Id = id;
        this.Name = name;
    }
    public string Id { get; set; }
    public string Name { get; set; }
    
};