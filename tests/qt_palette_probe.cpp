#include <QApplication>
#include <QPalette>
#include <QStyle>
#include <QTimer>
#include <QTextStream>
int main(int argc,char**argv){QApplication app(argc,argv);QTimer::singleShot(80,[&](){QTextStream out(stdout);auto p=app.palette();out<<"Qt="<<qVersion()<<" style="<<app.style()->objectName()<<" window="<<p.color(QPalette::Window).name()<<" text="<<p.color(QPalette::WindowText).name()<<" highlight="<<p.color(QPalette::Highlight).name()<<Qt::endl;app.quit();});return app.exec();}
