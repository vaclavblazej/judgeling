import React from 'react';

import { DividerMenuSubitem } from '../../api/menu';

interface Props {
  readonly subitem: DividerMenuSubitem;
}

const DividerDropdownElement: React.FC<Props> = ({ subitem }) => (
  <div className="dropdown-divider">
  </div>
);

export default DividerDropdownElement;
