import React, { FC } from 'react';

interface Properties {
  title: string;
}

const ServerStatus: FC<Properties> = ({ title }) => {
  const [isLoading, setIsLoading] = React.useState(true);
  const [message, setMessage] = React.useState("ok");

  React.useEffect(() => {
    const getData = () => {
      setIsLoading(true);
      fetch('http://ironviper-api.eu.ngrok.io/').then(m => m.json()).then(res => { 
        setIsLoading(false);
  
        let notificationsSocket = new WebSocket(res.notifications);
        notificationsSocket.onopen = function(evt) {
          console.log("Notifications websocket connected.");
        }
        notificationsSocket.onmessage = function(evt) {
          //console.log(evt.data);
          setMessage(evt.data);
        }
      });
    }

   getData();
  }, []);

  const render = <span>Server status: {message}</span>;
  const content = isLoading ? <div>Loading...</div> : <ul>{render}</ul>;

  return ( <div>{content}</div> );
};

export default ServerStatus;