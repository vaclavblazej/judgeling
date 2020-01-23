import React, {useEffect, useState} from 'react'
import {NavLink} from "react-router-dom";
import {getDirectory, ProblemDirectory} from "../api/api";

const ReactMarkdown = require('react-markdown')

const LoginPage: React.FC = () => {

  const [data, setData] = useState<ProblemDirectory>({'description': '', 'directories': []});
  useEffect(() => {
    getDirectory('/').then(value => {
      setData(value)
    });
  });


  const dirElements = data['directories'].map((dir) => (<tr>
    <th><NavLink to={dir}>{dir}</NavLink></th>
  </tr>));
  return (
    <div>
      <div>
        <ReactMarkdown source={data.description}/>
      </div>
      <div className="d-flex justify-content-center h-100">
        <div className="table-responsive">
          <table className="table table-striped table-sm">
            {/*<thead>*/}
            {/*<tr>*/}
            {/*  <th>Name</th>*/}
            {/*</tr>*/}
            {/*</thead>*/}
            <tbody>
            {dirElements}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
