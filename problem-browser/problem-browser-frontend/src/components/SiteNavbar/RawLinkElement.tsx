import React from 'react';

import {LinkMenuItem} from '../../api/menu';

interface Props {
  readonly linkMenuItem: LinkMenuItem;
}

const RawLinkElement: React.FC<Props> = ({linkMenuItem}) => {
  const link = linkMenuItem.link;

  return (
    <a className="nav-link" href={link}>
      {linkMenuItem.text}
    </a>
  );
};

export default RawLinkElement;
