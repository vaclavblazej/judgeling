import React, {useEffect, useState} from 'react'
import {getDirectory, ProblemDirectory} from "../api/api";
import Breadcrumbs, {BreadcrumbElement} from "../components/Breadcrumbs";
import ListBrowser, {BrowserElement} from "../components/ListBrowser";

const ReactMarkdown = require('react-markdown');

const prepareContent = (data: ProblemDirectory) => {
  if (data.content) {
    if (data.content_extension === '.md') {
      return (
        <div>
          <ReactMarkdown source={data.content}/>
        </div>
      );
    } else {
      return (<code style={{whiteSpace: 'pre-wrap'}}>{data.content}</code>);
    }
  } else {
    return (
      <p>
        This folder does not contain <code>index.md</code>, this file should contain either description of a problem or
        category description for sets of problems.
      </p>
    );
  }
};

const BrowsePage: React.FC = () => {

  const repository = 'acm-problems';

  const [address, setAddress] = useState<string[]>([repository, 'arrays', 'sort']);

  const [data, setData] = useState<ProblemDirectory>({'content': '', 'content_extension': '', 'directories': []});
  useEffect(() => {
    getDirectory(address).then(response => {
      setData(response);
    });
  }, [address]);

  const goBack = function (num: number): void {
    let s: string[] = address.slice();
    for (let i = 0; i < num; ++i) s.pop();
    setAddress(s)
  };

  let overview: JSX.Element[] = [];
  if (data.parts) {
    const paths = ['gen', 'val', 'jud', 'chk', 'sol', 'pic'];
    overview = paths.map((item) => {
      let style = 'btn-light';
      if (data.parts[item].length === 0) style = 'btn-danger';
      else if (data.parts[item].length >= 1) style = 'btn-success';
      return (
        <button key={item} type="button" className={'btn ' + style}>
          {item} <span className="badge badge-light">{data.parts[item].length}</span>
        </button>
      )
    });
  }

  let browser: BrowserElement[] = [];
  if (address.length > 1) {
    browser.push({
      text: '..', callback: () => {
        goBack(1);
      }
    });
  }
  browser = browser.concat(data['directories'].map((item) => {
    return {
      text: item,
      callback: () => {
        let s: string [] = address.slice();
        s.push(item);
        setAddress(s)
      }
    }
  }));

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
      <ListBrowser elements={browser}/>
      {prepareContent(data)}
      <div>
        {overview}
      </div>
    </>
  );
};

export default BrowsePage;
