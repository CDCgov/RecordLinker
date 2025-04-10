import Link from "next/link";
import styles from "./page.module.scss";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Record Linker</h1>
        <p>This is the landing page</p>
        <Link className="usa-button" href={"/wizard"}>
          Start wizard
        </Link>
      </main>
    </div>
  );
}
