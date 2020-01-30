import React from 'react';

export interface BrowserElement {
  readonly text: string;
  readonly callback?: () => void;
}

export interface Params {
  readonly elements: BrowserElement[];
}

const ListBrowser: React.FC<Params> = ({elements}) => {

  const dirElements = elements.map(({text, callback}) => {
      return <button key={text} type="button" className="btn btn-primary btn-sm btn-block text-left"
                     style={{marginTop: '0.6pt'}}
                     onClick={() => {
                       if (callback) callback()
                     }}>{text}</button>
    }
  );

  return (
    <div className="d-flex justify-content-center h-100" style={{flexFlow: 'column'}}>
      {dirElements}
    </div>
  )
};

export default ListBrowser;
