import React from 'react';

import { HeaderMenuSubitem } from '../../api/menu';

interface Props {
  readonly subitem: HeaderMenuSubitem;
}

const HeaderDropdownElement: React.FC<Props> = ({ subitem }) => (
  <h6 className="dropdown-header">
    {subitem.text}
  </h6>
);

export default HeaderDropdownElement;
