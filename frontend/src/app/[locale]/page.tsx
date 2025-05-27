import LanguagesSwitcher from "@/components/global/languageSwapper";
import ServerComponent from "@/components/server-components";

export default function Home() {
  return (
    <main className=" min-h-screen flex flex-col justify-center items-center  ">
      <div className="w-96">
        <LanguagesSwitcher />
        <ServerComponent />
      </div>
    </main>
  );
}