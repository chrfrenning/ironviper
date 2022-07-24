import React, { FC } from 'react';
import TreeView from '@mui/lab/TreeView';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import TreeItem from '@mui/lab/TreeItem';


interface TreeProps {
  items: any;
  cb : (item:any) => void;
}

const Tree: FC<TreeProps> = ({ items, cb }) => {
  function renderTree(n : any) {
    return <TreeItem key={n.id} nodeId={n.id} label={n.name} onClick={() => {cb(n);}}>
      { n.children && n.children.length > 0 && <ul>{n.children.map(renderTree)}</ul> }
    </TreeItem>
  }

  const treeRenderer = items.map( (n:any) => {
    return renderTree(n);
    // return <li key={n.id} 
    //     onClick={() => getData(n.name)}>
    //       <span title={n.title}>{n.name}</span>
    //   </li>;
  });

  const content = items.length == 0 ? <div>Loading...</div> : 
    <TreeView 
      aria-label="rich object"
      defaultCollapseIcon={<ExpandMoreIcon />}
      defaultExpanded={['root']}
      defaultExpandIcon={<ChevronRightIcon />}
      sx={{ height: 400, flexGrow: 1, maxWidth: 400, overflowY: 'auto'}}
    >
      {treeRenderer}
    </TreeView>;

  return ( <div>{content}</div> );
};

export default Tree;