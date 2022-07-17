import React, { FC } from 'react';

interface Properties {
  title: string;
}

const ServerStatus: FC<Properties> = ({ title }) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [message, setMessage] = React.useState("hello");

  React.useEffect(() => {
    getData();
  }, []);

  function getData() : void {
    setIsLoading(true);
    fetch('http://localhost:5211/').then(m => m.json()).then(res => { 
      title = res.notifications;
      setIsLoading(false);

      let websocket = new WebSocket(res.notifications);
      websocket.onopen = function(evt) {
        console.log("CONNECTED");
      }
      websocket.onmessage = function(evt) {
        console.log(evt.data);
        setMessage(evt.data);
      }

    });
  }

  const render = <span>{message}</span>;
  const content = isLoading ? <div>Loading...</div> : <ul>{render}</ul>;

  return ( <div>{content}</div> );
};

export default ServerStatus;