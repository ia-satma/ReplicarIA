/**
 * MobileNav.jsx - Navegación móvil
 *
 * Drawer deslizable desde la izquierda para:
 * - Navegación en dispositivos móviles y tablets
 * - Contiene la misma estructura de menú que el sidebar
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Menu } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../ui/sheet';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import { Separator } from '../ui/separator';
import { useSidebar } from './SidebarContext';
import { SidebarGroup } from './SidebarGroup';
import { NAVIGATION_CONFIG } from '../../config/navigation';

export function MobileNav() {
  const { isMobileOpen, toggleMobile, closeMobile } = useSidebar();

  return (
    <Sheet open={isMobileOpen} onOpenChange={toggleMobile}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="lg:hidden">
          <Menu className="w-6 h-6" />
          <span className="sr-only">Abrir menú</span>
        </Button>
      </SheetTrigger>

      <SheetContent side="left" className="w-80 p-0">
        <SheetHeader className="p-4 border-b border-gray-200 dark:border-gray-800">
          <SheetTitle className="flex items-center">
            <Link to="/" onClick={closeMobile}>
              <img
                src="/logo-revisar.png"
                alt="Revisar.ia"
                className="h-8 object-contain"
              />
            </Link>
          </SheetTitle>
        </SheetHeader>

        <ScrollArea className="h-[calc(100vh-80px)]">
          <nav className="p-4 space-y-1">
            {NAVIGATION_CONFIG.map((group, index) => (
              <React.Fragment key={group.id}>
                {/* forceExpanded=true para siempre mostrar labels en móvil */}
                <SidebarGroup group={group} forceExpanded={true} />
                {index < NAVIGATION_CONFIG.length - 1 && (
                  <Separator className="my-3" />
                )}
              </React.Fragment>
            ))}
          </nav>
        </ScrollArea>
      </SheetContent>
    </Sheet>
  );
}

export default MobileNav;
