import React from 'react';
import './App.css';
import Tree from './Tree';
import Items from './Items';
import ServerStatus from './ServerStatus';
import MainMenuBar from './MainMenuBar';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import InformationDrawer from './InformationDrawer';

export default function App() {
  const [currentFolder, setCurrentFolder] = React.useState("/");
  const [viewMode, setViewMode] = React.useState("grid");
  const [items, setItems] = React.useState([]);
  const [folders, setFolders] = React.useState([]);
  let i = 0;

  React.useEffect(() => {
    getFileItemsInCurrentFolder();
  }, []);

  function getFileItemsInCurrentFolder() {
    fetch(`http://ironviper-api.eu.ngrok.io/t${currentFolder}?d=1&i=true`)
    .then(m => m.json())
    .then(res => { 
      setItems(res.items); 
    }).catch(err => { console.log(err); });
  }

  React.useEffect(() => {
    getFullDepthTree();
  }, []);

  function getFullDepthTree() {
    fetch(`http://ironviper-api.eu.ngrok.io/t/?d=0`)
    .then(m => m.json())
    .then(res => { 
      setFolders(res.tree); 
    }).catch(err => { console.log(err); });
  }

  // function newFileItemHandler(item : any) : void {
  //   setItems( p => { return [ item, ...p ]; } );
  // }

  function onUserActionSelectFolder(path : string) : void {
    setCurrentFolder(path);
    setItems([]);
    getFileItemsInCurrentFolder();
  }

  function onUserActionPreviewItem(item : any) : void {
    // TODO: Switch view into preview mode
    console.log(item);
  }

  return (
    <div className="App">
      <MainMenuBar />
      <span>{currentFolder}</span>
      <ServerStatus title="Server Status"  />
      <Grid container spacing={2}>
        <Grid item xs={3}>
          <Tree items={folders} cb={(n) => {setCurrentFolder(n.name)}} />
        </Grid>
        <Grid item xs={9}>
          <Items items={items} />
        </Grid>
      </Grid>
    </div>
  );
}