import UploadFileContainer from "@/components/uploadFileContainer";

export default function Upload() {
  return (
    <>
      <div className="flex flex-col items-center h-screen mt-10">
        <h1 className="text-4xl font-bold mb-8">Dispatch Evaluation</h1>
        <div className="w-full">
          <UploadFileContainer />
        </div>
      </div>
    </>
  );
}
