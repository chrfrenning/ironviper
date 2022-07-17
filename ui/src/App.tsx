import React from 'react';
import logo from './logo.svg';
import './App.css';
import Tree from './Tree';
import Items from './Items';
import ServerStatus from './ServerStatus';

var current_path = "/";

function App() {

  return (
    <div className="App">
      <ServerStatus title="Server Status" />
      <Tree title={''} subtitle={''} />
      <Items items={[]} />
    </div>
  );
  
}

export default App;