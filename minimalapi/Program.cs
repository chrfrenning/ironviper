using System.Diagnostics;
using System.Net.Mime;
using System.Text;


var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();
var tree = Folder.LoadModelFromTable(app.Configuration["StorageConnectionString"]);
var file = File.LookupFileById("KK3-zkhZvGn", app.Configuration["StorageConnectionString"]);
Console.WriteLine("File" + file.Id + file.Name);

//TestModel();
PrintTree( tree );

app.MapGet("/", () => {
    return Results.Ok( new { 
        application="IronViper/0.1", 
        version="1.0", 
        tree="/t/(path)", 
        nodes="/n/(id)", 
        edges="/e/(type)", 
        source="https://github.com/chrfrenning/ironviper/", 
        copyright="IronViper Software is Copyright (C) Christopher Frenning 2022", 
        license="MIT",
        key = app.Configuration["StorageConnectionString"] 
        });
});

app.MapGet("/t/", () => {
    return tree.Children;
});

app.MapGet("/t/{*name}", (string name) => {
    Folder? folder = Folder.FindFolderByPath(tree, name);
    if ( folder == null )
        return Results.NotFound();
    
    return Results.Ok(folder.Children);
});

app.MapPut("/t/{*name}", (string name) => {
    Folder newFolder = Folder.CreateFolder(tree, name);
    return Results.Ok(newFolder);
});

app.MapDelete("/t/{*name}", (string name) => {
    Folder? folder = Folder.FindFolderByPath(tree, name);

    if ( folder == null )
        return Results.NotFound();

    if ( !Folder.CanDeleteFolder(folder) )
        return Results.BadRequest();

    Folder.DeleteFolder(folder);
    return Results.Ok();
});

app.MapGet("/tree", () => {
    StringBuilder sb = new StringBuilder();
    sb.Append("<html><body><ul>");
    FolderToHtml(tree, sb);
    
    sb.Append("</ul></body></html>");

    return Results.Extensions.Html(sb.ToString());

});

void FolderToHtml(Folder folder, StringBuilder sb) {
    sb.Append("<li>");
    sb.Append(folder.Name);
    sb.Append("<ul>");
    foreach ( var child in folder.Children ) {
        FolderToHtml(child, sb);
    }
    sb.Append("</ul>");
    sb.Append("</li>");
}

app.MapGet("/n/{id:regex(^[a-zA-Z0-9]{{7}}$)}", (string id) => {
    var folder = Folder.FindFolderById(tree, id);

    if ( folder == null )
        return Results.NotFound();

    return Results.Ok(folder);
});

app.MapGet("/n/{id:regex(^[a-zA-Z0-9]{{3}}-[a-zA-Z0-9]{{7}}$)}", (string id) => {
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

    Folder julia = root.AddChild( new Folder("Abcdefg", "julia") );
    julia.AddChild( new Folder("julia-1") );
    julia.AddChild( new Folder("julia-2") );

    root.AddChild( new Folder("seb") );

    return root;
}

void TestModel() {
    Folder root = CreateTestFolderTree();
    PrintTree( root );

    Debug.Assert( Folder.FindFolderById(root, "Abcdefg") != null );
    Debug.Assert( Folder.FindFolderByPath(root, "/julia/julia-1") != null );

    Folder folder = Folder.CreateFolder(root, "/julia/julia-2/julia-2-2/julia-2-2-2");
    PrintTree( root );

    Folder.DeleteFolder(root, "/julia/julia-2/julia-2-2/julia-2-2-2");
    PrintTree( root );
    
}

void PrintTree(Folder root, int level = 0) {
    Console.WriteLine(new String('-', level) + root.Name + " (" + root.Id + ")");
    foreach (var child in root.Children) {
        PrintTree(child, level + 1);
    }
}

static class ResultsExtensions
{
    public static IResult Html(this IResultExtensions resultExtensions, string html)
    {
        ArgumentNullException.ThrowIfNull(resultExtensions);

        return new HtmlResult(html);
    }
}

class HtmlResult : IResult
{
    private readonly string _html;

    public HtmlResult(string html)
    {
        _html = html;
    }

    public Task ExecuteAsync(HttpContext httpContext)
    {
        httpContext.Response.ContentType = MediaTypeNames.Text.Html;
        httpContext.Response.ContentLength = Encoding.UTF8.GetByteCount(_html);
        return httpContext.Response.WriteAsync(_html);
    }
}