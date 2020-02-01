import React from 'react';
import {BrowserRouter, Route, Switch} from 'react-router-dom';

import SiteNavbar from './components/SiteNavbar/SiteNavbar';
import BrowsePage from "./pages/BrowsePage";

const App: React.FC = () => {

  return (
    <BrowserRouter>
      <div id="App">
        <SiteNavbar foundCallback={(found => console.log(found))}/>
        <main className="container-fluid container-body">
          <Switch>
            <Route exact path="/" component={BrowsePage}/>
            <Route exact path="/problems" component={BrowsePage}/>
          </Switch>
        </main>
      </div>
    </BrowserRouter>
  );
};

export default App;
