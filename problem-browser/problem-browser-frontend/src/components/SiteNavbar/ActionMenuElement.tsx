import React from 'react';

import {ActionMenuSubitem} from '../../api/menu';

interface Props {
  readonly actionMenuSubitem: ActionMenuSubitem;
}

const ActionMenuElement: React.FC<Props> = ({actionMenuSubitem}) => {
  return (
    <button className="dropdown-item" onClick={() => actionMenuSubitem.action()}>
      {actionMenuSubitem.text}
    </button>
  );
};

export default ActionMenuElement;
