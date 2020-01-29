import React from 'react';

export interface Props {
  readonly elements: BreadcrumbElement[];
}

export interface BreadcrumbElement {
  readonly text: string;
  readonly callback?: any;
}

const Breadcrumbs: React.FC<Props> = ({elements}) => {

  const breadcrumbs = [elements.map((item, index) => {
    const content = item.callback ? (
      <a href="#" onClick={() => item.callback()}>{item.text}</a>
    ) : (
      <span>{item.text}</span>
    );
    return (<li key={index} className={"breadcrumb-item" + (item.callback ? '' : ' active')}>{content}</li>)
  })];

  return (
    <nav aria-label="breadcrumb">
      <ol className="breadcrumb">
        {breadcrumbs}
      </ol>
    </nav>
  )
};

export default Breadcrumbs;
