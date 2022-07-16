import React, { FC } from 'react';
import "./Items.css";

interface ItemProps {
  items : any
}

const Items: FC<ItemProps> = ({  }) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [items, setItems] = React.useState([]);

  React.useEffect(() => {
    getData();
  }, []);

  function getData(): void {
    setIsLoading(true);
    fetch('http://localhost:5211/t/?d=1&i=true').then(m => m.json()).then(res => { console.log(res); setIsLoading(false); setItems(res.items); });
  }

  const itemsRenderer = items.map( (n:any) => {
    return <div className="item" id={n.id} key={n.id}>
          <div className="thumbnail">
            <img src={n.thumbnailUrl} title={n.title} alt={n.description} />
          </div>
          <div className="info">
            <span className="filename">{n.name}.{n.extension}</span>
          </div>
        </div>;
  });

  const content = isLoading ? <div className="itemGrid">Loading...</div> : <div className="itemGrid">{itemsRenderer}</div>;

  return ( <div>{content}</div> );
};

export default Items;