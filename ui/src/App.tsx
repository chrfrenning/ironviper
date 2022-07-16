import React from 'react';
import logo from './logo.svg';
import './App.css';
import Tree from './Tree';
import Items from './Items';

var current_path = "/";

function App() {

  return (
    <div className="App">
      <Tree title={''} subtitle={''} />
      <Items items={[]} />
      {/* <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        
      </header> */}
    </div>
  );
  
}

export default App;
