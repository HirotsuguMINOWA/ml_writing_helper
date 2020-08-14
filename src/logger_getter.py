""" Log """
import logging
from logging import Formatter, StreamHandler, FileHandler, DEBUG, INFO


#
# logger = None

def get_logger(
        name
        , level_console=logging.INFO
        , log_format='%(asctime)s [%(levelname)s] %(message)s'
        , logfile_path=''
        , level_file=logging.INFO
):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create file handler which logs even DEBUG messages
    if logfile_path != "":
        fh = logging.FileHandler(logfile_path)
        fh.setLevel(level_file)
        # fh_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(name)s - %(funcName)s - %(message)s')
        fh_formatter = logging.Formatter(log_format, '%Y-%m-%d %H:%M:%S')
        fh.setFormatter(fh_formatter)

    # create console handler with a INFO log level
    ch = logging.StreamHandler()
    ch.setLevel(level_console)
    # ch_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%Y-%m-%d %H:%M:%S')
    ch_formatter = logging.Formatter(log_format, '%Y-%m-%d %H:%M:%S')
    ch.setFormatter(ch_formatter)

    # add the handlers to the logger
    if logfile_path != "":
        logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
#     ##### Config of root
#     #     filename  Specifies that a FileHandler be created, using the specified
#     #               filename, rather than a StreamHandler.
#     #     filemode  Specifies the mode to open the file, if filename is specified
#     #               (if filemode is unspecified, it defaults to 'a').
#     #     format    Use the specified format string for the handler.
#     #     datefmt   Use the specified date/time format.
#     #     style     If a format string is specified, use this to specify the
#     #               type of format string (possible values '%', '{', '$', for
#     #               %-formatting, :meth:`str.format` and :class:`string.Template`
#     #               - defaults to '%').
#     #     level     Set the root logger level to the specified level.
#     #     stream    Use the specified stream to initialize the StreamHandler. Note
#     #               that this argument is incompatible with 'filename' - if both
#     #               are present, 'stream' is ignored.
#     #     handlers  If specified, this should be an iterable of already created
#     #               handlers, which will be added to the root handler. Any handler
#     #               in the list which does not have a formatter assigned will be
#     #               assigned the formatter created in this function.
#     #     force     If this keyword  is specified as true, any existing handlers
#     #               attached to the root logger are removed and closed, before
#     #               carrying out the configuration as specified by the other
#     #               arguments.
#     logging.basicConfig(level=level)
#     # print(f"[Debug-Debug] name:{name}")
#     # log_format += f"@{name}"
#     # global logger
#     # if logger is not None:
#     #     return logger
#     # create loggery --------------------------------------------------------------------
#
#     # import logging.handlers  # for logrotate用handlerの取得
#
#     # 基本的な設定の実施 ---------------------------------------------------------------
#     # 基本的なLoggingの設定を行う．つまり，handler個別にLevel, Formatを指定しなくても良くなる
#     # logging.basicConfig() # default設定を「全てのhandler」へ適用
#     # loggery = None
#     # def make_logger():
#     #     import logging
#     #     return loggery
#     #
#     # loggery = make_logger()
#     # logging.basicConfig(  # 「全てのhandler」のLevel, Formatを指定
#     #     filename=logfile_path
#     #     , level=level_stream  # 表示する
#     #     # , format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     #     , format=log_format
#     # )
#     # loggery = logging.getLogger(name)
#
#     # loggery.info("Detected Platform: " + platform_name)
#     # 各種ハンドラー設定 ---------------------------------------------------------------
#     # いずれに出力するか？を指定
#
#     ## コンソール出力: create console handler and set level to debug
#     # loggingの設定でコンソールに出力するのに，下記と併記すると2重にlog表示
#     # ch = logging.StreamHandler()
#     # ch.setLevel(logging.DEBUG)
#     # logging.addHandler(ch)  # handlerでroot loggerへ追加
#
#     ## ファイル出力:create file handler which logs even debug messages
#     # if to_file:
#     #     fh = logging.FileHandler(logfile_path)
#     #     fh.setLevel(level_stream)
#     #     logging.addHandler(fh)  # handlerでroot loggerへ追加
#
#     ## logのローテートの設定
#     # TimedRotatingFileHandler(filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False, atTime=None)
#
#     # formatterの「個別」指定．
#     # ※ BasicConfigを使って一括指定した場合，下記不要
#     # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     # ch.setFormatter(formatter)
#     # fh.setFormatter(formatter)
#     # lh.setFormatter(formatter)
#
#     # module別にlevel指定．-------------------------------------------
#     # これにより,logから消す事ができる
#     # logging.getLogger('sqlalchemy').setLevel(logging.INFO) # sqlalchemy全部のlevel指定.DEBUGだとすごい量のLOG放出
#     # 個別指定．http://docs.sqlalchemy.org/en/latest/core/engines.html
#     # loggery.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
#     # loggery.getLogger('sqlalchemy.dialects').setLevel(logging.CRITICAL)
#     # loggery.getLogger('sqlalchemy.pool').setLevel(logging.CRITICAL)
#     # loggery.getLogger('sqlalchemy.orm').setLevel(logging.CRITICAL)
#
#     # -------------------------------------------------------------------------------------------------------------
#
#     # --------------------------------
#     # 1.loggerの設定
#     # --------------------------------
#     # loggerオブジェクトの宣言
#     logger = logging.getLogger(name)
#
#     # loggerのログレベル設定(ハンドラに渡すエラーメッセージのレベル)
#     # loggery.setLevel(logging.DEBUG)
#     # logger.setLevel(level_stream)
#
#     # --------------------------------
#     # 2.handlerの設定
#     # --------------------------------
#
#     # handler_format.default_msec_format = '%s.%03d'
#     # handler_format.default_msec_format = '%s'  # ミリ秒の削除 -> Errorとなる
#     # logging.basicConfig(level=level_stream, format=log_format)
#
#     # ログ出力フォーマット設定
#     # handler_format = Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#
#     handler_format = Formatter(log_format)
#     if to_file:
#         #######################################################
#         ##
#         ## ファイル出力:create file handler which logs even debug messages
#         ##
#         fh = FileHandler(logfile_path)
#         fh.setLevel(level)
#         fh.setFormatter(handler_format)
#         logger.addHandler(fh)  # handlerでroot loggerへ追加
#     else:
#         #######################################################
#         ##
#         ## Stream(Console) handlerの生成
#         ##
#         sh = StreamHandler()
#         # handlerのログレベル設定(ハンドラが出力するエラーメッセージのレベル)
#         sh.setLevel(level_stream)
#         sh.setFormatter(handler_format)
#         # 3.loggerにhandlerをセット
#         logger.addHandler(sh)
#         del sh
#
#     # --------------------------------
#     # ログ出力テスト
#     # --------------------------------
#     # loggery.debug("Hello World!")
#
#     return logger
#     # return None
#
# # loggery = get_logger()
