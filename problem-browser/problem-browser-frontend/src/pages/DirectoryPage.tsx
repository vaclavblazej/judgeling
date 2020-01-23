import React from 'react';
import {NavLink} from "react-router-dom";

const LoginPage: React.FC = () => {

  return (
    <div>
      <div className="d-flex justify-content-center h-100">
        <div className="card">
          <div className="card-header">
            <h3>Přihlášení</h3>
          </div>
          <div className="card-body">
            <form>
              <div className="input-group form-group">
                <input type="text" className="form-control" placeholder="Emailová adresa"/>
              </div>
              <div className="input-group form-group">
                <input type="password" className="form-control" placeholder="Heslo"/>
              </div>
              {/*<div className="row align-items-center form-group remember">*/}
              {/*  <input type="checkbox"/>Pamatovat si přihlášení*/}
              {/*</div>*/}
            </form>
          </div>
          <div className="card-footer">
            <div className="d-flex justify-content-center links">
              Chcete vytvořit nový účet? <NavLink to="/registrace">Registrovat</NavLink>
            </div>
            <div className="d-flex justify-content-center">
              <NavLink to="/reset">Zapomenuté heslo?</NavLink>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
