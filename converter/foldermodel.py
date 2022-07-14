import shortuuid
from azure.data.tables import TableClient

#
# TODO: As the folder structure grows to big sizes, it is not efficient to load
# the structure every time the converter starts. Caching it in memory is not a good
# idea as it is likely to be stale (user creates folder, then initiates upload).
# Instead we should take the "overhead" of finding the root, then walking
# through queries to find the folder in question. This will result in n=depth
# queries, but it will be faster than loading the entire structure every time and
# avoid the caching problem alltogether.
#
# The challenge now is finding the root. One way of fixing this is to have a
# fixed id for the root, e.g. 'OorootO'

class Folder:
    def __init__(self, id, name):
        if id is None:
            id = shortuuid.random(length=7)

        self.id = id
        self.name = name
        self.children = []
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)
        self.children.sort(key=lambda x: x.name)

    def get_root(self):
        if self.parent is None:
            return self
        else:
            return self.parent.get_root()

    def get_path(self):
        path = ""
        n = self
        while n is not None:
            name = n.name
            if name == "/":
                name = ""
            path = name + "/" + path
            n = n.parent
        return path

def FindFolderByName(flat_folder_list, name):
    for f in flat_folder_list:
        if f.name == name:
            return f
    
    return None

def FindFolderById(flat_folder_list, id):
    for f in flat_folder_list:
        if f.id == id:
            return f
    
    return None

def FindFolderByParentId(flat_folder_list, parentId):
    for f in flat_folder_list:
        if f.parentId == parentId:
            return f
    
    return None

def FindFolderByPath(startFolder, path):
    if path[0] == '/':
        startFolder = startFolder.get_root()

    for part in path.split('/'):
        if part == '':
            continue
        startFolder = FindFolderByName(startFolder.children, part)
        if startFolder is None:
            return None

    return startFolder

def LoadAllFoldersFromAzureTable(conn_str):
    table_name = "forest"
    queue_table = TableClient.from_connection_string(conn_str, table_name)
    query_results_iterator = queue_table.query_entities("PartitionKey eq 'folder'")
    
    all_folders_flat = []
    for entity in query_results_iterator:
        print(entity)
        new_folder = Folder(entity['RowKey'], entity['Name'])
        new_folder.parentId = entity['Parent']
        all_folders_flat.append( new_folder )
        
    return all_folders_flat

def CreateFolderTreeFromFlatFolderList(flat_folder_list):
    root = FindFolderByName(flat_folder_list, "/")
    flat_folder_list.remove(root)

    AddChildFolders(root, flat_folder_list)
    assert len(flat_folder_list) == 0
    return root

def AddChildFolders(parent, flat_folder_list):
    c = FindFolderByParentId(flat_folder_list, parent.id)
    while c is not None:
        parent.add_child(c)
        flat_folder_list.remove(c)
        AddChildFolders(c, flat_folder_list)
        c = FindFolderByParentId(flat_folder_list, parent.id)

def AddFolderToModelAndDatabase(parentFolder, newFolderName, conn_str):
    if FindFolderByName(parentFolder.children, newFolderName) is not None:
        raise Exception("Folder already exists")
    newFolder = Folder(None, newFolderName)
    newFolder.parent = parentFolder
    while not IsIdUnique(parentFolder.get_root(), newFolder.id):
        newFolder.id = shortuuid.random(length=7)
    AddFolderToDatabase(newFolder, conn_str)
    parentFolder.add_child(newFolder)
    return newFolder

def AddFolderToDatabase(folder, conn_str):
    table_name = "forest"
    table_client = TableClient.from_connection_string(conn_str, table_name)
    entity = {
        'PartitionKey': 'folder',
        'RowKey': folder.id,
        'Name': folder.name,
        'Parent': folder.parent.id if folder.parent is not None else None
    }
    table_client.create_entity(entity)

def IsIdUnique(root,id):
    for f in root.children:
        if f.id == id:
            return False
    return True

def PrintFolder(folder, level=0):
    p = "-" * level
    print(p + folder.name)
    for child in folder.children:
        PrintFolder(child,level+1)

conn_str = "DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net;AccountName=ironviper006d20b7;AccountKey=GFEJ6h5NV0nUcsJT8J3MF5zUnYtWMnOEwgTaRH8lUKb+3pVvOyiNkuzwT/jS1F7FDuAMe0VFzv2d+ASt/1gKvw==;BlobEndpoint=https://ironviper006d20b7.blob.core.windows.net/;FileEndpoint=https://ironviper006d20b7.file.core.windows.net/;QueueEndpoint=https://ironviper006d20b7.queue.core.windows.net/;TableEndpoint=https://ironviper006d20b7.table.core.windows.net/"
folders_flat = LoadAllFoldersFromAzureTable(conn_str)
root = CreateFolderTreeFromFlatFolderList(folders_flat)
PrintFolder(root)

f = FindFolderByPath(root, "/folder1/folder1-1")
if f is not None:
    print(f.name)
    print(f.get_path())

print(Folder(None, "/").get_path())

f = AddFolderToModelAndDatabase(root, "folder2", conn_str)
AddFolderToModelAndDatabase(f, "folder2-1", conn_str)
AddFolderToModelAndDatabase(f, "folder2-2", conn_str)
AddFolderToModelAndDatabase(f, "folder2-3", conn_str)