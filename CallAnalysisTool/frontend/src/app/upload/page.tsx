import UploadFileContainer from "@/components/uploadFileContainer";

export default function Upload() {
  return (
    <>
      <div className="flex flex-col items-center h-screen overflow-hidden">
        <h1 className="text-4xl font-bold mb-8 mt-10">Dispatch Evaluation</h1>
        <div className="w-full flex-1 overflow-hidden flex flex-col">
          <UploadFileContainer />
        </div>
      </div>
    </>
  );
}
