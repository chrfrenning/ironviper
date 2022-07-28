import React, { FC } from 'react';
import Dropzone from 'react-dropzone';
import Box from '@mui/material/Box';
import ImageList from '@mui/material/ImageList';
import ImageListItem from '@mui/material/ImageListItem';
import ImageListItemBar from '@mui/material/ImageListItemBar';
import "./Items.css";

interface ItemProps {
  items : any
}

const Items: FC<ItemProps> = ({ items }) => {

  const content = <section>
    <Dropzone noClick onDrop={ acceptedFiles => {
              acceptedFiles.map( (file:any) => {
                //console.log(file);
                
                let path = undefined;
                console.log(file.path);
                if ( file.path.indexOf("/") > -1 ) {
                  path = file.path.substring(0, file.path.lastIndexOf("/"));
                } else {
                  path = "/";
                }
                
                fetch(`https://ironviper-api.eu.ngrok.io/services/initialize-upload/?path=${path}&filename=${file.name}`)
                .then(m => m.json()).then(res => { 
                  //console.log(res);
                  fetch(res.url, { method: 'PUT', body: file, mode: 'cors', headers: {
                    'x-ms-version': '2019-12-12',
                    'x-ms-blob-type': 'BlockBlob',
                    'x-ms-blob-content-type': file.type,
                    'x-ms-meta-original_filename': file.name,
                    'x-ms-meta-uniqueid': res.id
                  }}).then( res => console.log(res) );
              });

              return file;
          });
          }}>
            {({ getRootProps, getInputProps }) => (
              <section>
                <div {...getRootProps({
                      //onClick: event => event.stopPropagation(),
                    })}>
                  <input {...getInputProps()} />
                    <Box sx={{ }}>
                      <ImageList variant="standard" gap={5} cols={6} rowHeight={200}>
                        {items.map((itm : any) => (
                          <ImageListItem key={itm.id}>
                            <img
                              src={`${itm.thumbnailUrl}`}
                              srcSet={`${itm.thumbnailUrl} 2x`}
                              alt={itm.title}
                              loading="lazy"
                            />
                          </ImageListItem>
                        ))}
                      </ImageList>
                    </Box>
                  </div>
                  </section>
            )}
            </Dropzone>
            
    </section>;

  return ( <div>{content}</div> );
};

export default Items;