import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function Header() {
  return (
    <header className="site-header">
      <div className="container header-inner">
        <div className="brand">
          <div className="brand-icon">
            <ShieldCheck size={26} />
          </div>
          <div>
            <h1 className="brand-title">Karnataka Electoral Notice Checker</h1>
            <p className="brand-subtitle">
              Official public search tool for notices published by the Chief Electoral Officer, Karnataka.
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}


