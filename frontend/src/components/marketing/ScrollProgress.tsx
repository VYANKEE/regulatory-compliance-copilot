import { motion, useScroll, useSpring } from 'framer-motion'

/** Fixed 2px progress hairline at the very top of the viewport. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll()
  const scaleX = useSpring(scrollYProgress, { stiffness: 120, damping: 24, mass: 0.2 })
  return (
    <motion.div
      style={{ scaleX, transformOrigin: '0% 50%' }}
      className="fixed left-0 top-0 z-[60] h-[2px] w-full bg-gradient-to-r from-[var(--signal)] to-[var(--cyan)]"
    />
  )
}
