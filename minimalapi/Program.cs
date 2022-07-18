using System.Diagnostics;
using System.Net.Mime;
using System.Text;
using Azure.Messaging.WebPubSub;
using Azure.Storage;
using Azure.Storage.Blobs;
using Azure.Storage.Sas;
using Microsoft.AspNetCore.Mvc;

var builder = WebApplication.CreateBuilder(args);
builder.Services.AddCors(options => {
    options.AddDefaultPolicy( p => {
        p.AllowAnyOrigin();
        p.AllowAnyHeader();
        p.AllowAnyMethod();
    });
});
var app = builder.Build();
app.UseCors( options => {
    options.AllowAnyOrigin();
    options.AllowAnyHeader();
    options.AllowAnyMethod();
});

var tree = Folder.LoadModelFromTable(app.Configuration["StorageConnectionString"]);
var file = File.LookupFileById("KK3-zkhZvGn", app.Configuration["StorageConnectionString"]);
if ( file != null ) 
    Console.WriteLine("File" + file.Id + " " + file.Name);

//TestModel();
PrintTree( tree );

string GetWebPubSubClientUrl() {
    const string HUBNAME = "notifications";

    var connectionString = app.Configuration["PubSubConnectionString"];
    var serviceClient = new WebPubSubServiceClient(connectionString, HUBNAME);
    var uri = serviceClient.GetClientAccessUri(DateTime.UtcNow.AddDays(30));
    return uri.ToString();
}

app.MapGet("/", () => {
    return Results.Ok( new { 
        application="IronViper/1.0", 
        version="1.0", 
        ptree="/t/(path)", 
        nodes="/n/(id)", 
        vertices="/v/(type)",
        edges="/e/(vertex)/",
        app_license="MIT",
        app_source="https://github.com/chrfrenning/ironviper/", 
        app_copyright=$"IronViper is Copyright (C) Christopher Frenning 2020-{DateTime.UtcNow.Year}",
        notifications=GetWebPubSubClientUrl()
        });
});

// app.MapGet("/t/", () => {
//     dynamic m = new { t = tree.Children, i = new List<dynamic>() };
//     return Results.Ok(m);
// });

app.MapGet("/t/{*name}", (string? name, [FromQuery(Name="d")]int? depth, [FromQuery(Name="i")]bool? includeItems) => {
    Folder? folder = tree;
    if ( name != null )
        folder = Folder.FindFolderByPath(tree, name);

    if ( folder == null )
        return Results.NotFound();

    var realDepth = depth ?? 0;
    if ( realDepth == 0 )
        realDepth = int.MaxValue;
    folder = folder.CloneToDepth(realDepth);

    List<File> itemsInFolder = new List<File>();
    if ( includeItems != null && includeItems == true )
        itemsInFolder = folder.ListAllFiles(app.Configuration["StorageConnectionString"]);

    dynamic info = new {
            id = folder.Id,
            name = folder.Name,
            hasChildren = folder.HasChildren,
            title = folder.Title,
            description = folder.Description,
            tags = folder.Tags
        };

    dynamic m = new { 
        info = info,
        tree = folder.Children, 
        items = itemsInFolder 
        };

    return Results.Ok(m);
});

app.MapPut("/t/{*name}", (string name) => {
    Folder newFolder = Folder.CreateFolder(tree, name, app.Configuration["StorageConnectionString"]);
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

app.MapGet("/f/{id}", (string id) => {
    Folder? folder = Folder.FindFolderById(tree, id);
    if ( folder == null )
        return Results.NotFound();

    return Results.Redirect("/t" + folder.Path);
});

app.MapGet("/i/{id}", (string id) => {
    File? file = File.LookupFileById(id, app.Configuration["StorageConnectionString"]);
    if ( file == null )
        return Results.NotFound();
    // TODO: Redirect this to the /t/<path>/<filename> endpoint
    return Results.Ok(file);
});

app.MapGet("/tree/{*name}", (string? name) => {
    Folder? folder = tree;
    if ( name != null )
        folder = Folder.FindFolderByPath(tree, name);
    if ( folder == null )
        return Results.NotFound();

    StringBuilder sb = new StringBuilder();
    sb.Append("<html><body>");
    
    sb.Append("<ul id='tree'>");
    FolderToHtml(folder, sb);
    sb.Append("</ul>");

    sb.Append("<ul id='items'>");
    bool anyFiles = false;
    folder.ListAllFiles(app.Configuration["StorageConnectionString"]).ForEach(f => {
        anyFiles = true;
        sb.Append($"<li><a href='/i/{f.Id}'><img src='{f.ThumbnailUrl}'><br/>{f.Name}</a></li>");
    });
    sb.Append("</ul>");

    if ( !anyFiles ) {
        sb.Append("<p>No files in this folder. Drop one or more here to get started.</p>");
    }

    sb.Append("</body></html>");

    return Results.Extensions.Html(sb.ToString());
});

void FolderToHtml(Folder folder, StringBuilder sb) {
    sb.Append("<li>");
    sb.AppendFormat("<a href='/tree{0}'>", folder.Path);
    sb.Append(folder.Name);
    sb.Append("</a>");
    sb.Append("<ul>");
    foreach ( var child in folder.Children ) {
        FolderToHtml(child, sb);
    }
    sb.Append("</ul>");
    sb.Append("</li>");
}

string CreateSasTokenWithFilename(Folder folder, string filename) {
    const string CONTAINER_NAME = "file-store";
    
    BlobContainerClient container = new BlobContainerClient(app.Configuration["StorageConnectionString"], CONTAINER_NAME);
    var client = container.GetBlobClient(folder.Path + "/" + filename );
    return client.GenerateSasUri(BlobSasPermissions.Create, DateTimeOffset.UtcNow.AddMinutes(5)).ToString();
}

string CreateSasToken(Folder folder) {
    return CreateSasTokenWithFilename(folder, IDGenerator.Generate(16));
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

app.MapGet("/services/initialize-upload", (string path, string? filename) => {
    // TODO: Introduce count parameter to retrieve multiple tokens at once.
    Folder? folder = Folder.FindFolderByPath(tree, path);
    if ( folder == null )
        folder = Folder.CreateFolder(tree, path, app.Configuration["StorageConnectionString"]);

    string sasToken;
    if ( filename != null ) {
        // TODO: Check if the filename is already used in this folder    
        sasToken = CreateSasTokenWithFilename(folder, filename);
    } else {
        // we're assigning a random filename
        sasToken = CreateSasToken(folder);
    }

    dynamic result = new {
        id = CreateUniqueIDForFile(),
        url = sasToken,
        expires = DateTime.UtcNow.AddMinutes(5).ToString("yyyy-MM-ddTHH:mm:ssZ")
    };
    
    return Results.Ok(result);
});

string CreateUniqueIDForFile() {
    string uniqueId = IDGenerator.Generate(10);
    uniqueId = uniqueId.Substring(0,3) + "-" + uniqueId.Substring(3);
    return uniqueId;
}

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