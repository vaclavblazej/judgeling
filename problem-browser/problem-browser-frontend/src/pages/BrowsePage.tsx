import React, {useEffect, useState} from 'react'
import {ProblemDirectory} from "../api/api";
import Breadcrumbs, {BreadcrumbElement} from "../components/Breadcrumbs";

const ReactMarkdown = require('react-markdown');

const BrowsePage: React.FC = () => {

  const repository = 'acm-problems';

  const [address, setAddress] = useState<string[]>([repository, 'arrays', 'sort']);

  const [data, setData] = useState<ProblemDirectory>({'content': '', 'content_extension': '', 'directories': []});
  useEffect(() => {
    fetch("api/problem/" + address.slice(1).join('/')).then(response => {
      response.json().then((res) => {
        setData(res);
      });
    });
  }, [address]);

  const goBack = function (num: number): void {
    let qq: string[] = address.slice();
    for (let i = 0; i < num; ++i) qq.pop();
    setAddress(qq)
  };

  let goBackElement = (<></>);
  if (address.length > 1) { // is present only if we are not in the root directory
    goBackElement = (
      <button type="button" className="btn btn-primary btn-sm btn-block text-left" style={{marginTop: '1pt'}}
              onClick={() => {
                goBack(1);
              }}>..</button>
    );
  }
  const dirElements = data['directories'].map((dir: string) => (
    <button key={dir} type="button" className="btn btn-primary btn-sm btn-block text-left" style={{marginTop: '1pt'}}
            onClick={() => {
              setAddress(address.concat([encodeURI(dir)]));
            }}>{dir}</button>
  ));
  let markdown;
  if (data.content) {
    if (data.content_extension === '.md') {
      markdown = (
        <div>
          <ReactMarkdown source={data.content}/>
        </div>
      );
    } else {
      markdown = (<code style={{whiteSpace: 'pre-wrap'}}>{data.content}</code>);
    }
  } else {
    markdown = (
      <p>
        This folder does not contain <code>index.md</code>, this file should contain either description of a problem or
        category description for sets of problems.
      </p>
    );
  }
  let overview: JSX.Element[] = [];
  if (data.parts) {
    const paths = ['gen', 'val', 'jud', 'chk', 'sol', 'pic'];
    overview = paths.map((item) => {
      let style = 'btn-light';
      if (data.parts[item].length === 0) style = 'btn-danger';
      else if (data.parts[item].length === 1) style = 'btn-primary';
      else if (data.parts[item].length >= 1) style = 'btn-success';
      return (
        <button type="button" className={'btn ' + style}>
          {item} <span className="badge badge-light">{data.parts[item].length}</span>
        </button>
      )
    });
  }
  const breadcrumbs: BreadcrumbElement[] = address.map((item, index) => {
    if (index !== address.length - 1) {
      return {text: item, callback: () => goBack(address.length - index - 1)}
    } else {
      return {text: item};
    }
  });

  return (
    <>
      <Breadcrumbs elements={breadcrumbs}/>
      <div className="d-flex justify-content-center h-100" style={{flexFlow: 'column'}}>
        {goBackElement}
        {dirElements}
      </div>
      {markdown}
      <div>
        {overview}
      </div>
    </>
  );
};

export default BrowsePage;
