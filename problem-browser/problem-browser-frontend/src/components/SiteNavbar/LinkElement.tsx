import React from 'react';
import { NavLink } from 'react-router-dom';

import { LinkMenuItem } from '../../api/menu';

interface Props {
  readonly linkMenuItem: LinkMenuItem;
}

const SiteNavbarElementLink: React.FC<Props> = ({ linkMenuItem }) => {
  const link = linkMenuItem.link;

  return (
    <NavLink className="nav-link" to={link} exact={'/' === link}>
      {linkMenuItem.text}
    </NavLink>
  );
};

export default SiteNavbarElementLink;
