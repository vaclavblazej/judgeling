import {inferType} from './utils';

export type MenuItemType = 'LINK' | 'DROPDOWN' | 'RAWLINK';

export interface MenuItem {
  readonly text: string;
  readonly itemType: MenuItemType;
  readonly id: number;
}

export interface LinkMenuItem extends MenuItem {
  readonly link: string;
}

export interface DropdownMenuItem extends MenuItem {
  readonly subitems: MenuSubitem[];
}

export type MenuSubitemType = 'LINK' | 'HEADER' | 'DIVIDER' | 'ACTION';

export interface MenuSubitem {
  readonly itemType: MenuSubitemType;
  readonly id: number;
}

export interface LinkMenuSubitem extends MenuSubitem {
  readonly text: string;
  readonly link: string;
}

export interface ActionMenuSubitem extends MenuSubitem {
  readonly text: string;
  readonly action: () => void;
}

export interface HeaderMenuSubitem extends MenuSubitem {
  readonly text: string;
}

export interface DividerMenuSubitem extends MenuSubitem {
}

export function navigationMenu(): MenuItem[] {
  return [
    inferType({
      text: 'Browse',
      itemType: 'LINK',
      link: '/problems',
      id: 1,
    }),
  ];
}

export function loginMenu(): MenuItem[] {
  return [inferType({
    text: 'Přihlásit se',
    itemType: 'LINK',
    link: '/prihlaseni',
    id: 90,
  }),
    {
      text: 'Registrovat',
      itemType: 'LINK',
      link: '/registrace',
      id: 91,
    }
  ];
}
