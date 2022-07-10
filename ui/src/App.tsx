import React from 'react';
import logo from './logo.svg';
import './App.css';
import Tree from './Tree';

var current_path = "/";

function App() {

  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <Tree title={''} subtitle={''} />
      </header>
    </div>
  );
  
}

export default App;
