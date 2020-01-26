// export type SubmissionStatusType = 'SUBMITTED' | 'WRONG_ANSWER' | 'CORRECT' | 'TO_BE_CORRECTED';

export interface ProblemDirectory {
  readonly content: string;
  readonly content_extension: string;
  readonly directories: string[];
}

/*export interface Year {
  readonly id?: number;
  readonly name: string;
  readonly rounds: RoundPreview[];
}*/

// TODO: fetch from API
export async function getDirectory(directoryAddr?: string[]): Promise<ProblemDirectory> {
  if (directoryAddr === undefined) directoryAddr = [''];
  console.log(directoryAddr);
  const headers = {method: 'get', headers: new Headers({'Content-Type': 'application/json'})};
  return fetch("localhost/problem" + directoryAddr.join('/'), headers).then(response => {
    if (!response.ok) throw Error(response.statusText)
    return response.body as any;
  });
  // console.log(res);
  // return {
  //   content: "## Arrays\nProblems in this category exploit arrays.\nThis sorting, searching, etc. \n\n",
  //   directories: ["arrays.md", "binsearch", "kthmin", "lis", "long_segment_with_increasing_bounds", "sort"]
  // }
}

/*
export async function getTask(taskId: number, roundId?: number, yearId?: number): Promise<Task> {
  return {
    id: 193,
    name: 'První úkol',
    points: 10,
    userSubmissions: [
      {
        id: 9324,
        submittedTime: new Date(2019, 10, 1, 20, 43),
        status: 'CORRECT',
        points: 10,
      },
      {
        id: 9321,
        submittedTime: new Date(2019, 10, 1, 20, 2),
        status: 'WRONG_ANSWER',
        points: 4,
      },
    ],
  };
}
*/
