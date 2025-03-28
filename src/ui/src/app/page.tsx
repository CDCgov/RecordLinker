import styles from './page.module.scss';
import { Button } from '@trussworks/react-uswds';

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <h1>Record Linker</h1>
        <p>Hello world!</p>
        <Button>Test button</Button>
      </main>
    </div>
  );
}
