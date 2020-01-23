import React from 'react';
import {Link} from 'react-router-dom';

import {navigationMenu} from '../../api/menu';
import MenuItemElement from './MenuItemElement';

const SiteNavbar: React.FC = () => {

  const navigationMenuItems = navigationMenu().map((menuItem) => (
    <MenuItemElement menuItem={menuItem} key={menuItem.id}/>
  ));

  return (
    <nav className="navbar navbar-expand-md navbar-dark bg-dark" id="site-navbar">
      <div className="container-fluid">
        <Link to="/" className="navbar-brand">Problem browser</Link>

        <button type="button" className="navbar-toggler ml-auto" data-toggle="collapse"
                data-target="#site-header-collapse">
          <span className="navbar-toggler-icon"/>
        </button>

        <div className="collapse navbar-collapse" id="site-header-collapse">
          <ul className="navbar-nav mr-auto">
            {navigationMenuItems}
          </ul>
          <div className="dropdown-divider"/>
        </div>
      </div>
    </nav>
  );
};

export default SiteNavbar;
