import React, {useEffect, useState} from 'react'
import {getDirectory, ProblemDirectory} from "../api/api";

const ReactMarkdown = require('react-markdown');

const BrowsePage: React.FC = () => {

  const [address, setAddress] = useState<string[]>(['']);

  const [data, setData] = useState<ProblemDirectory>({'content': '', 'content_extension': '', 'directories': []});
  useEffect(() => {
    fetch("api/problem" + address.join('/')).then(response => {
      response.json().then((res) => {
        setData(res);
      });
    });
  }, [address]);


  let goBackElement = (<></>);
  if (address.length > 1) { // is present only if we are not in the root directory
    goBackElement = (
      <tr>
        <th><a href='#' onClick={() => {
          let qq: string[] = address.slice();
          qq.pop();
          setAddress(qq)
        }}>..</a></th>
      </tr>
    );
  }
  const dirElements = data['directories'].map((dir: string) => (
    <tr key={dir}>
      <th><a href='#' onClick={() => setAddress(address.concat([encodeURI(dir)]))}>{dir}</a></th>
    </tr>
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

  return (
    <div>
      <div className="d-flex justify-content-center h-100">
        <div className="table-responsive">
          <table className="table table-striped table-sm">
            <tbody>
            {goBackElement}
            {dirElements}
            </tbody>
          </table>
        </div>
      </div>
      {markdown}
    </div>
  );
};

export default BrowsePage;
