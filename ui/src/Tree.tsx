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
    current_path = "";
    setIsLoading(true);
    fetch('http://localhost:5211/t/?d=0' + current_path).then(m => m.json()).then(res => { setIsLoading(false); setTree(res.tree); });
  }

  const onclick = (e: any) => {
    getData("/aja");
  }

  function renderTree(n : any) {
    return <li key={n.id} title={n.title}>
      {n.name}
      { n.children && n.children.length > 0 && <ul>{n.children.map(renderTree)}</ul> }
    </li>
  }

  const treeRenderer = tree.map( (n:any) => {
    return renderTree(n);
    // return <li key={n.id} 
    //     onClick={() => getData(n.name)}>
    //       <span title={n.title}>{n.name}</span>
    //   </li>;
  });

  const content = isLoading ? <div>Loading...</div> : <ul>{treeRenderer}</ul>;

  return ( <div>{content}</div> );
};

export default Tree;