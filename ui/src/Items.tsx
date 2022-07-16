import React, { FC } from 'react';
import {useCallback} from 'react';
import Dropzone from 'react-dropzone';
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

  const content = isLoading ? <div className="itemGrid">Loading...</div> : <section>
    <Dropzone onDrop={ acceptedFiles => {
              acceptedFiles.map( (file:any) => {
                console.log(file);
                console.log("Uploading " + file.name);
                fetch('http://localhost:5211/services/initialize-upload/?path=/&filename='+file.name)
                .then(m => m.json()).then(res => { 
                  console.log(res);
                  fetch(res.url, { method: 'PUT', body: file, mode: 'cors', headers: {
                    'x-ms-version': '2019-12-12',
                    'x-ms-blob-type': 'BlockBlob',
                    'x-ms-blob-content-type': file.type,
                    'x-ms-meta-original_filename': file.name,
                    'x-ms-meta-uniqueid': res.id
                  }}).then( res => console.log(res) );
              });
          });
          }}>
            {({ getRootProps, getInputProps }) => (
              <section>
                <div {...getRootProps()}>
                  <input {...getInputProps()} />
                  <p>Drag'n'drop files here to upload</p>
                  </div>
                  </section>
            )}
            </Dropzone>
            <div className="itemGrid">{itemsRenderer}</div>
    </section>;

  return ( <div>{content}</div> );
};

export default Items;