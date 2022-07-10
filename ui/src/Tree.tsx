import React, { FC } from 'react';

interface TreeProps {
  title: string;
  subtitle: string;
}

const Tree: FC<TreeProps> = ({ title, subtitle }) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [tree, setTree] = React.useState([]);
  var current_path = "/";

  React.useEffect(() => {
    getData(current_path);
  }, []);

  function getData(path: string): void {
    current_path += "/" + path;
    setIsLoading(true);
    fetch('http://localhost:5211/t/' + current_path).then(m => m.json()).then(res => { console.log(res.t[0].id); setIsLoading(false); setTree(res.t); });
  }

  const onclick = (e: any) => {
    getData("/aja");
  }

  const treeRenderer = tree.map( (n:any) => {
    return <li key={n.id} onClick={() => getData(n.name)}>{n.name}</li>;
  });

  const content = isLoading ? <div>Loading...</div> : <ul>{treeRenderer}</ul>;

  return ( <div>{content}</div> );
};

export default Tree;