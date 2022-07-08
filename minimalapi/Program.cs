var tree = CreateTestFolderTree();
var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.MapGet("/", () => "IronViper/0.1");

app.MapGet("/folders", () => {
    return tree.Children;
});

app.MapPut("/folders/{name}", (string name) => {
    Folder root = tree;

    // check if the name is unique
    Folder? folder = root.Children.Find(f => f.Name == name);
    if (folder != null) {
        throw new ApplicationException("Name already exists");
    }
    // create a new folder
    folder = new Folder(name);
    root.Children.Add(folder);
    return folder.Id;
});

app.MapDelete("/folders/{name}", (string name) => {
    Folder root = tree;
    Folder? folder = root.Children.Find(f => f.Name == name);
    if (folder == null) {
        throw new ApplicationException("Folder not found");
    }
    root.Children.Remove(folder);
    return folder.Id;
});

app.MapGet("/t/", () => {
    return tree.Children;
});


app.MapGet("/t/{*name}", (string name) => {
    Folder? node = tree;

    foreach( var part in name.Split('/') ) {
        if (part == "") {
            continue;
        }

        node = node.Children.Find(f => f.Name == part);

        if (node == null)
            return Results.NotFound();
    }

    return Results.Ok(node.Children);
});

app.MapGet("/i/{id}", (string id) => {
    var folder = Folder.FindFolderById(tree, id);

    if ( folder == null )
        return Results.NotFound();

    return Results.Ok(folder);
});

app.Run();
    
Folder CreateTestFolderTree() {
    
    Folder root = new Folder("/");

    root.AddChild( new Folder("aja") );
    root.AddChild( new Folder("chris") );
    root.AddChild( new Folder("jacob") );

    Folder julia = root.AddChild( new Folder("julia") );
    julia.AddChild( new Folder("julia-1") );
    julia.AddChild( new Folder("julia-2") );

    root.AddChild( new Folder("seb") );

    return root;
}