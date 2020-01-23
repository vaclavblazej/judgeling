import React from 'react';

import {
  DropdownMenuItem, HeaderMenuSubitem, LinkMenuSubitem, DividerMenuSubitem, ActionMenuSubitem
} from '../../api/menu';

import LinkDropdownElement from './LinkDropdownElement';
import HeaderDropdownElement from './HeaderDropdownElement';
import DividerDropdownElement from './DividerDropdownElement';
import ActionMenuElement from "./ActionMenuElement";

interface Props {
  dropdownMenuItem: DropdownMenuItem;
}

const DropdownElement: React.FC<Props> = ({ dropdownMenuItem }) => {
  const content = dropdownMenuItem.subitems.map((subitem) => {
    const itemType = subitem.itemType;
    if ('DIVIDER' === itemType) {
      return <DividerDropdownElement key={subitem.id}
                                     subitem={subitem as DividerMenuSubitem} />;
    } else if ('HEADER' === itemType) {
      return <HeaderDropdownElement key={subitem.id}
                                    subitem={subitem as HeaderMenuSubitem} />;
    } else if('LINK' === itemType) {
      return <LinkDropdownElement key={subitem.id}
                                  subitem={subitem as LinkMenuSubitem} />;
    } else if ('ACTION' === itemType) {
      return <ActionMenuElement key={subitem.id}
                                actionMenuSubitem={subitem as ActionMenuSubitem} />;
    } else {
      return null;
    }
  });
  // FIXME: replace #/ with something accessible
  return (
    <>
    <a className="nav-link dropdown-toggle" href="#/" role="button"
       data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
       {dropdownMenuItem.text}
    </a>
    <div className="dropdown-menu">
      {content}
    </div>
    </>
  );
};

export default DropdownElement;
