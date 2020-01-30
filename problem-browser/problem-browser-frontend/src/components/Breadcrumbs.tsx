import React from 'react';

export interface Props {
  readonly elements: BreadcrumbElement[];
}

export interface BreadcrumbElement {
  readonly text: string;
  readonly callback?: () => void;
}

const Breadcrumbs: React.FC<Props> = ({elements}) => {

  const breadcrumbs = [elements.map(({text, callback}, index) => {
    const content = callback ? (
      <a href="#" onClick={() => {
        if (callback) callback()
      }}>{text}</a>
    ) : (
      <span>{text}</span>
    );
    return (<li key={index} className={"breadcrumb-item" + (callback ? '' : ' active')}>{content}</li>)
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
