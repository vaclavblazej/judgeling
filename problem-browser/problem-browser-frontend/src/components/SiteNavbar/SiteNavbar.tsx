import React, {useState} from 'react';
import {Link} from 'react-router-dom';

import {navigationMenu} from '../../api/menu';
import MenuItemElement from './MenuItemElement';
import {FontAwesomeIcon} from '@fortawesome/react-fontawesome'
import {faSearch} from '@fortawesome/free-solid-svg-icons'
import {searchProblems} from "../../api/api";

export interface Params {
  readonly foundCallback?: (found: string[]) => any;
}

const SiteNavbar: React.FC<Params> = ({foundCallback}) => {

  const navigationMenuItems = navigationMenu().map((menuItem) => (
    <MenuItemElement menuItem={menuItem} key={menuItem.id}/>
  ));

  const [query, setQuery] = useState('');

  const searchElement = foundCallback ? (
    <form className="form-inline input-group md-form form-sm form-2 pl-0">
      <input className="form-control my-0 py-0" type="text" placeholder="Search" aria-label="Search"
             onChange={(event => setQuery(event.target.value))}/>
      <div className="input-group-append">
        <button type="button" className="input-group-text red lighten-3"
                onClick={() => searchProblems(query).then(response => foundCallback(response))}>
          <FontAwesomeIcon icon={faSearch}/>
          {/*<i className="fas fa-search text-grey" aria-hidden="true"/>*/}
        </button>
      </div>
    </form>
  ) : (<></>);

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
          {searchElement}
        </div>
      </div>
    </nav>
  );
};

export default SiteNavbar;
