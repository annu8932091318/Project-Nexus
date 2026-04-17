import { runSkillRuntime } from '../src/services/skillsApi';

async function main(): Promise<void> {
  const result = await runSkillRuntime('generate project plan from approved charter');
  console.log(JSON.stringify(result));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
