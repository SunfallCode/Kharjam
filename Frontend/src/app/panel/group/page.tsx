"use client";

import { Button } from "@/components/ui/button";

const GroupPage = () => {
  return (
    <>
      <div className="flex justify-between items-center mt-8">
        <div>{`<`}</div>
        <div className="text-center">
          <p>my groups</p>
          <p>3 active groups</p>
        </div>
        <div>switch button</div>
      </div>
      <div className="grid grid-cols-2 gap-2 mt-6">
        <div className="bg-green-200 h-40 rounded-xl"></div>
        <div className="bg-red-300 h-40 rounded-xl"></div>
      </div>
      <div className="h-40 bg-back-secondary my-6 rounded-xl flex items-center justify-center">
        charts here
      </div>
      <div className="rounded-xl bg-back-secondary p-4">
        <div className="flex items-center justify-between mb-5">
            <p>active groups</p>
            <Button>new group</Button>
        </div>
        <div className="bg-input h-20 rounded-lg"></div>
        <div className="bg-input h-20 rounded-lg my-5"></div>
        <div className="bg-input h-20 rounded-lg"></div>
      </div>
    </>
  );
};
export default GroupPage;
