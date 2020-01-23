import React from 'react';
import { Link } from 'react-router-dom';

import { LinkMenuSubitem } from '../../api/menu';

interface Props {
  subitem: LinkMenuSubitem;
}

const LinkDropdownElement: React.FC<Props> = ({ subitem }) => (
  <Link className="dropdown-item" to={subitem.link}>
    {subitem.text}
  </Link>
);

export default LinkDropdownElement;
