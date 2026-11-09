#include <QApplication>
#include <QTimer>
#include <QPalette>
#include <QSettings>
#include <QTextStream>
#include <QFile>
int main(int argc,char **argv){QApplication app(argc,argv);QString config=argv[1],scheme=argv[2];QTimer::singleShot(250,[=](){QSettings colors(scheme,QSettings::IniFormat);for(QString group:{"active_colors","inactive_colors","disabled_colors"}){auto values=colors.value("ColorScheme/"+group).toStringList();values[12]="#ff88aaff";colors.setValue("ColorScheme/"+group,values);}colors.sync();QSettings settings(config,QSettings::IniFormat);settings.setValue("Appearance/pixel_theme_revision",1);settings.sync();});QTimer::singleShot(4300,[&](){auto color=app.palette().color(QPalette::Highlight).name();QTextStream(stdout)<<"Qt="<<qVersion()<<" live highlight="<<color<<Qt::endl;app.exit(color=="#88aaff"?0:1);});return app.exec();}
