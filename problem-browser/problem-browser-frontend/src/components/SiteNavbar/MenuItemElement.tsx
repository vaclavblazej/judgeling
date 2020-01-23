import React from 'react';

import { MenuItem, LinkMenuItem, DropdownMenuItem } from '../../api/menu';
import LinkElement from './LinkElement';
import DropdownElement from './DropdownElement';
import RawLinkElement from "./RawLinkElement";

interface Props {
  readonly menuItem: MenuItem;
}

const MenuItemElement: React.FC<Props> = ({ menuItem }) => {
  const itemType = menuItem.itemType;

  const classes = ['nav-item'];
  if ('DROPDOWN' === itemType) {
    classes.push('dropdown');
  }

  let content;
  if ('DROPDOWN' === itemType) {
    content = <DropdownElement dropdownMenuItem={menuItem as DropdownMenuItem} />;
  } else if ('LINK' === itemType) {
    content = <LinkElement linkMenuItem={menuItem as LinkMenuItem} />;
  } else if ('RAWLINK' === itemType) {
    content = <RawLinkElement linkMenuItem={menuItem as LinkMenuItem} />;
  }
  return (
    <li className={classes.join(' ')}>
      {content}
    </li>
  );
};

export default MenuItemElement;
