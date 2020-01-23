import React, {useState} from 'react';

export interface PaginationBounds {
  readonly total: number;
  readonly pageSize: number;
  readonly initialPage?: number;
  readonly onChange?: (first: number, afterLast: number) => void;
}

const Pagination: React.FC<PaginationBounds> = ({total, pageSize, initialPage, onChange}) => {

  if (initialPage === undefined) initialPage = 0;
  const [currentPage, setCurrentPage] = useState(initialPage);
  const pagesTotal = Math.floor((total + pageSize - 1) / pageSize);
  if (currentPage < 0) setCurrentPage(0);
  if (currentPage >= pagesTotal) setCurrentPage(pagesTotal - 1);

  const range = 2;
  let numberList = [];
  for (let i = Math.max(0, currentPage - range); i <= Math.min(pagesTotal - 1, currentPage + range); i++) {
    numberList.push(i);
  }
  const list = numberList.map((number) => {
      if (number === currentPage) {
        return (<button key={number} type="button" className="btn btn-outline-dark" disabled={true}>{number + 1}</button>)
      } else {
        return (<button key={number} type="button" className="btn btn-dark"
                        onClick={() => setCurrentPage(number)}>
          {number + 1}
        </button>)
      }
    }
  );


  if (onChange) onChange(currentPage * pageSize, Math.min(total, (currentPage + 1) * pageSize));

  const isFirst = currentPage === 0;
  const isLast = currentPage === pagesTotal - 1;

  return (
    <div className="pagination">
      <button type="button" className="btn btn-dark" disabled={isFirst}
              onClick={() => setCurrentPage(0)}>
        first
      </button>
      <button type="button" className="btn btn-dark" disabled={isFirst}
              onClick={() => setCurrentPage(currentPage - 1)}>
        prev
      </button>
      {list}
      <button type="button" className="btn btn-dark" disabled={isLast}
              onClick={() => setCurrentPage(currentPage + 1)}>
        next
      </button>
      <button type="button" className="btn btn-dark" disabled={isLast}
              onClick={() => setCurrentPage(pagesTotal - 1)}>
        last
      </button>
    </div>
  )
};

export default Pagination;
